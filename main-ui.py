import requests
import time
import queue
from enum import Enum
from threading import Thread, Lock, Condition 
from config import *

# ------------------------------------
# for the server comms
message_queue = queue.Queue()

# for the core program
crate = [0] * CRATE_CAPACITY
highest_empty_slot = 0
total_collected_fruits = 0
pickers_synchronizer = 0
slot_reserving_lock = Lock()
full_crate_notifier = Condition(Lock())
empty_crate_notifier = Condition(Lock())
# --------------------------------------

# Server comm helpers ------------------
class EventType(Enum):
    start_truck_load = 1
    empty_crate = 2
    check_for_a_slot = 3
    wait_for_a_slot = 4
    pick_fruit_and_add_to_crate = 5
  
def http_worker():
    """Consumes the queue and sends POST requests to Flask."""
    while True:
        state = message_queue.get()
        if state == "SHUTDOWN":
            break
        try:
            requests.post(FLASK_URL, json=state, timeout=5)
        except Exception as e:
            print(f"HTTP Error: {e}")
        message_queue.task_done()

def _send_action(actor, event_type: EventType, crate_slot: int = None, picker_uid=None):
    """FIX: Now puts state into a queue; worker thread handles the POST request."""
    state = {
        "actor": actor,
        "uid": picker_uid,
        "event": str(event_type),
        "crate_slot_number": crate_slot,
        "fruits_picked": total_collected_fruits,
        "crate": crate.copy(), # Send a copy to avoid mutation issues
        "total_fruits": TOTAL_FRUITS,
    }
    message_queue.put(state)
# -----------------------------------

# Program helpers ------------------------
def do_work(duration_sec, busy_wait: bool=BUSY_WAIT_IN_DO_WORK):
  if busy_wait:
    start = time.time()
    while (time.time() - start) <= duration_sec:
        _ = 100*10
  else:
    time.sleep(duration_sec)

def _log(actor, action):
  print(f"[{actor}]: {action}")

def get_highest_empty_slot():
  global highest_empty_slot, total_collected_fruits
  if highest_empty_slot == CRATE_CAPACITY or total_collected_fruits == TOTAL_FRUITS:
    # a slot is not available
    return None
  else:
    # reserve this slot
    highest_empty_slot += 1
    total_collected_fruits += 1
    return highest_empty_slot - 1

def all_fruits_collected(): # for clarity
  return total_collected_fruits >= TOTAL_FRUITS

def reset_crate():
  global highest_empty_slot, crate
  highest_empty_slot = 0
  crate = [0] * CRATE_CAPACITY

# ------------------------------------------

# Program thread functions -----------------------------
def picker_task(uid):
  global highest_empty_slot, pickers_synchronizer
  
  def log(action):
    _log(f"PICKER {uid}", action)
  
  def send_action(event_type: EventType, slot=None):
     _send_action(
        "PICKER", event_type, slot, uid
     )

  def synchronize(exit: bool = False):
    global pickers_synchronizer
    log("Waiting for the crate to empty.")
    pickers_synchronizer += 1
    if pickers_synchronizer == PICKER_COUNT:
      log("All Pickers are waiting, waking up the Loader.")
      # this is the last thread
      pickers_synchronizer = 0
      with full_crate_notifier:
        full_crate_notifier.notify()
    if not exit:
      empty_crate_notifier.wait()

  while True:
    # request a slot to place the fruit
    log("Attempting to reserve a slot in the crate.")
    send_action(EventType.check_for_a_slot)
    with slot_reserving_lock:
      slot = get_highest_empty_slot()

    if slot is None:
      log("An empty slot wasn't found in the crate.")
      send_action(EventType.wait_for_a_slot)
      
      with empty_crate_notifier:
        if all_fruits_collected():
          synchronize(exit=True)
          log("All fruits have been collected from the tree. Exiting.")
          break
        else:
          log("The crate is full, waiting for other Pickers.")
          synchronize()
          continue

    send_action(EventType.pick_fruit_and_add_to_crate, slot) 
    do_work(CRATE_LOADING_TIME)
    log(f"Placed fruit in the crate. (Slot #{slot})")
    crate[slot] = 1


def loader_task():
    global total_collected_fruits, highest_empty_slot

    def log(action):
      _log(f"LOADER", action)

    def send_action(event_type: EventType):
       _send_action("LOADER", event_type)

    while True:

      with full_crate_notifier:

        while highest_empty_slot < CRATE_CAPACITY and total_collected_fruits < TOTAL_FRUITS:
          full_crate_notifier.wait()

        log("Woken up by all the Pickers. Emptying the crate.")
        send_action(EventType.start_truck_load)

        do_work(TRUCK_LOADING_TIME)
        reset_crate()

        send_action(EventType.empty_crate)
        log("Emptied the crate, notifying the Pickers.")
        log(f"Fruits collected: ({total_collected_fruits})")

      with empty_crate_notifier:  
        empty_crate_notifier.notify_all()

      if total_collected_fruits == TOTAL_FRUITS:
        log("All fruits have been collected. Signing off.")
        break
  
if __name__ == "__main__":
  t_http = Thread(target=http_worker,daemon=True)
  t_http.start()
  loader_t = Thread(target=loader_task)
  loader_t.start()

  pickers = []
  for uid in range(PICKER_COUNT): 
    picker_t = Thread(target=picker_task, args=(uid,))
    pickers.append(picker_t)
  for picker in pickers: 
    picker.start()
  for picker in pickers:
    picker.join()
  loader_t.join()

  print("Waiting for final messages to send to Flask...")
  message_queue.join()
  print("Done. All data propagated.")   