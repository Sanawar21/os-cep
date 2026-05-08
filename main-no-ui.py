import time
from threading import Thread, Lock, Condition 
from config import *

crate = [0] * CRATE_CAPACITY
highest_empty_slot = 0
total_collected_fruits = 0
pickers_synchronizer = 0

def do_work(duration_sec, busy_wait: bool=True):
  if busy_wait:
    start = time.time()
    while (time.time() - start) <= duration_sec:
        _ = 100*10
  else:
    time.sleep(duration_sec)

def _log(actor, action):
  print(f"[{actor}]: {action}")

def reset_crate():
  global highest_empty_slot, crate
  highest_empty_slot = 0
  crate = [0] * CRATE_CAPACITY


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

slot_reserving_lock = Lock()
full_crate_notifier = Condition(Lock())
empty_crate_notifier = Condition(Lock())


def picker_task(uid):
  global highest_empty_slot, pickers_synchronizer
  
  def log(action):
    _log(f"PICKER {uid}", action)

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
    with slot_reserving_lock:
      slot = get_highest_empty_slot()

    if slot is None:
      log("An empty slot wasn't found in the crate.")
      
      with empty_crate_notifier:
        if all_fruits_collected():
          synchronize(exit=True)
          log("All fruits have been collected from the tree. Exiting.")
          break
        else:
          log("The crate is full, waiting for other Pickers.")
          synchronize()
          continue 
    
    do_work(CRATE_LOADING_TIME)
    log(f"Placed fruit in the crate. (Slot #{slot})")
    crate[slot] = 1

def loader_task():
    global total_collected_fruits, highest_empty_slot

    def log(action):
      _log(f"LOADER", action)


    while True:

      with full_crate_notifier:

        while highest_empty_slot < CRATE_CAPACITY and total_collected_fruits < TOTAL_FRUITS:
          full_crate_notifier.wait()

        log("Woken up by all the Pickers. Emptying the crate.")

        do_work(TRUCK_LOADING_TIME)
        reset_crate()

        log("Emptied the crate, notifying the Pickers.")
        log(f"Fruits collected: ({total_collected_fruits})")

      with empty_crate_notifier:  
        empty_crate_notifier.notify_all()

      if total_collected_fruits == TOTAL_FRUITS:
        log("All fruits have been collected. Signing off.")
        break


if __name__ == "__main__":
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


