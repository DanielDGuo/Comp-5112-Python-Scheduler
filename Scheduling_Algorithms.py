import random as r
import math

# Set seed
r.seed(0)

# Constants for job generation
NUM_JOBS = 100
MIN_ARRIVAL = 0
MAX_ARRIVAL = 400
MIN_LENGTH = 1
MAX_LENGTH = 100

# Constants for online estimate generation
MU1 = 2.0 # upper bound of the estimate; mu1 * job length
MU2 = 2.0 # lower bound of the estimate; job length / mu2
# Setting MU1 to 1 and MU2 to 1/E will place the estimation between the signal time and the job's length
E = .35 # the estimate is given after e to 1 - e of the job's length has been processed

# Job Representation
class Job:
    def __init__(self, arrival, length):
        self.arrival = arrival
        self.length = length
        self.processing = 0

    def process(self):
        self.processing += 1
        
    def remaining(self):
        return self.length - self.processing

    def is_complete(self):
        return self.length == self.processing

    def reset_processing(self):
        self.processing = 0

    def __str__(self):
        return f"Arrival: {self.arrival}, Processing: {self.processing}/{self.length}"

class JobWithEstimate(Job):
    def __init__(self, arrival, length, estimate, signal_after):
        super().__init__(arrival, length)
        self.estimate = estimate
        self.signal_after = signal_after
    def __init__(self, job):
        super().__init__(job.arrival, job.length)

        self.estimate = r.randint(int(MU2 * self.length), int(MU1 * self.length))
        self.signal_after = int(r.uniform(E, 1 - E) * self.length)
    def __str__(self):
        return f"Arrival: {self.arrival}, Processing: {self.processing}/{self.length}, Estimate: {self.estimate}, Signal After: {self.signal_after}"

# SRPT Implementation
def SRPT(jobs):
    schedule = []
    completion_times = {}
    time = 0

    while any(not job.is_complete() for job in jobs):
        # Get all jobs that have arrived and are not complete
        available_jobs = [job for job in jobs if job.arrival <= time and not job.is_complete()] 

        if available_jobs:
            # Get minimum remaining time job, tie-breaking on arrival time
            job = min(available_jobs, key=lambda candidate: (candidate.remaining(), candidate.arrival))
            job.process()
            schedule.append((time, jobs.index(job)))

            if job.is_complete():
                completion_times[job] = time + 1
        else:
            schedule.append((time, None))

        time += 1

    # Calculate total flow time for comparison with other scheduling algorithms
    total_flow_time = sum(completion_times[job] - job.arrival for job in jobs)
    return schedule, total_flow_time

# Multilevel Feedback Queue Implementation
def MLFQ(jobs):
    # Helper function to calculate a job's queue based on its processing time.
    def get_MLFQ_job_queue(job):
        return math.floor(math.log2(job.processing + 2)) - 1

    queues = [[]]
    completion_times = {}
    schedule = []
    time = 0

    while any(not job.is_complete() for job in jobs):
        for job in jobs:
            # Add new jobs to the first queue when they arrive
            if job.arrival == time and not job.is_complete():
                queues[0].append(job)

        # Select the first non-empty queue
        selected_queue = None
        for index, queue in enumerate(queues):
            if queue:
                selected_queue = index
                break

        # If no queue has jobs, idle
        if selected_queue is None:
            schedule.append((time, None, None))
            time += 1
            continue

        # Process the job at the front of the selected queue
        job = queues[selected_queue].pop(0)
        job.process()
        schedule.append((time, jobs.index(job), selected_queue))

        # If the job is complete, record its completion time
        if job.is_complete():
            completion_times[job] = time + 1
        # Otherwise, determine its next queue and add it back to the appropriate queue.
        else:
            queue_index = get_MLFQ_job_queue(job)
            while len(queues) <= queue_index:
                queues.append([])
            queues[queue_index].append(job)

        time += 1

    total_flow_time = sum(completion_times[job] - job.arrival for job in jobs)
    return schedule, total_flow_time

# Balanced MLFQ Implementation
def Balanced_MLFQ(jobs):

    # Helper function to calculate a job's class based on its elapsed time, estimate, and signal_after.
    def get_Balanced_MLFQ_job_class(job):
        if job.processing < job.signal_after:
            job_class = math.ceil(math.log2(job.processing + 1))
        # If the job has reached or exceeded the signal_after point, we use the elapsed time to determine its class.
        else:
            job_class = max(math.ceil(math.log2(job.processing + 1)), 1 + math.floor(math.log2(job.estimate)))

        return job_class
    
    # Helper function to update a job's class and return whether it has increased.
    def update_class(job):
        new_class = get_Balanced_MLFQ_job_class(job)
        old_class = job_classes[job]
        job_classes[job] = new_class
        return new_class > old_class

    QOngoing = []
    QFresh = []
    schedule = []
    completion_times = {}
    job_classes = {job: get_Balanced_MLFQ_job_class(job) for job in jobs}
    time = 0

    while any(not job.is_complete() for job in jobs):
        # Add new jobs to the fresh queue when they arrive
        for job in jobs:
            if job.arrival == time and not job.is_complete():
                QFresh.append(job)

        # Update job classes and move jobs from ongoing to fresh if their class has increased
        for job in list(QOngoing) + list(QFresh):
            if update_class(job) and job in QOngoing:
                QOngoing.remove(job)
                QFresh.append(job)

        # Balance Phase: Promote a job from QFresh to QOngoing if they have a lower class than the minimum class in QOngoing and if the number of fresh jobs is at least 1/4 of the total active jobs.
        active_count = len(QOngoing) + len(QFresh)
        if len(QFresh) > 0:
            min_fresh_class = min(job_classes[job] for job in QFresh)
            min_ongoing_class = min((job_classes[job] for job in QOngoing), default=float("inf"))

            if min_fresh_class < min_ongoing_class and len(QFresh) >= active_count / 4:
                promoted_job = min(QFresh, key=lambda job: job_classes[job])
                QFresh.remove(promoted_job)
                QOngoing.append(promoted_job)

        # Process Phase: Select the job with the minimum class from QOngoing and process it.
        if len(QOngoing) > 0:
            job = min(QOngoing, key=lambda candidate: job_classes[candidate])
            schedule.append((time, jobs.index(job), job_classes[job]))
            job.process()

            if job.is_complete():
                completion_times[job] = time + 1
                QOngoing.remove(job)
            else:
                if update_class(job):
                    QOngoing.remove(job)
                    QFresh.append(job)
        # If there are no jobs in QOngoing, idle
        else:
            schedule.append((time, None, None))
        time += 1

    total_flow_time = sum(completion_times[job] - job.arrival for job in jobs)
    return schedule, total_flow_time

def print_test():
    # Create a list of jobs by sorted arrival time
    jobs = []
    for _ in range(NUM_JOBS):
        arrival = r.randint(MIN_ARRIVAL, MAX_ARRIVAL)
        length = r.randint(MIN_LENGTH, MAX_LENGTH)
        jobs.append(Job(arrival, length))
    jobs.sort(key=lambda j: j.arrival)

    # Print the list of jobs
    print("\n".join(f"Job {jobs.index(job)}: {str(job)}" for job in jobs))

    # Perform SRPT scheduling
    schedule, total_flow_time = SRPT(jobs)
    print("\nSRPT schedule:")
    for time, job_index in schedule:
        if job_index is None:
            print(f"Time {time}: idle")
        else:
            print(f"Time {time}: job {job_index}")
    print(f"Total flow time: {total_flow_time}")

    # Reset processing for other scheduling algorithms
    for job in jobs:
        job.reset_processing()

    # Perform MLFQ scheduling
    schedule, total_flow_time = MLFQ(jobs)
    print("\nMLFQ schedule:")
    for time, job_index, queue_index in schedule:
        if job_index is None:
            print(f"Time {time}: idle")
        else:
            print(f"Time {time}: job {job_index} (queue {queue_index})")
    print(f"Total flow time: {total_flow_time}")

    # Reset processing for other scheduling algorithms
    for job in jobs:
        job.reset_processing()

    # Create a list of jobs by sorted arrival time
    MLFQjobs = []
    for job in jobs:
        MLFQjobs.append(JobWithEstimate(job))
    MLFQjobs.sort(key=lambda j: j.arrival)

    # Print the list of jobs with estimates
    print("\n".join(f"Job {MLFQjobs.index(job)}: {str(job)}" for job in MLFQjobs))

    # Perform Balanced MLFQ scheduling
    schedule, total_flow_time = Balanced_MLFQ(MLFQjobs)
    print("\nBalanced MLFQ schedule:")
    for time, job_index, queue_index in schedule:
        if job_index is None:
            print(f"Time {time}: idle")
        else:
            print(f"Time {time}: job {job_index} (queue {queue_index})")
    print(f"Total flow time: {total_flow_time}")

def full_test():
    num_runs = 1000
    average_srpt_flow_time = 0
    average_mlfq_flow_time = 0
    average_balanced_mlfq_flow_time = 0

    max_srpt_flow_time = 0
    max_mlfq_flow_time = 0
    max_balanced_mlfq_flow_time = 0

    num_times_balanced_mlfq_better = 0
    for x in range(num_runs):
        if x % (num_runs // 10) == 0:
            print(f"Run {x}/{num_runs}")
        # Create a list of jobs by sorted arrival time
        jobs = []
        for _ in range(NUM_JOBS):
            arrival = r.randint(MIN_ARRIVAL, MAX_ARRIVAL)
            length = r.randint(MIN_LENGTH, MAX_LENGTH)
            jobs.append(Job(arrival, length))
        jobs.sort(key=lambda j: j.arrival)


        # Perform SRPT scheduling
        schedule, SRPT_total_flow_time = SRPT(jobs)
        average_srpt_flow_time += SRPT_total_flow_time/num_runs
        max_srpt_flow_time = max(max_srpt_flow_time, SRPT_total_flow_time)

        # Reset processing for other scheduling algorithms
        for job in jobs:
            job.reset_processing()

        # Perform MLFQ scheduling
        schedule, MLFQ_total_flow_time = MLFQ(jobs)
        average_mlfq_flow_time += MLFQ_total_flow_time/num_runs
        max_mlfq_flow_time = max(max_mlfq_flow_time, MLFQ_total_flow_time)

        # Reset processing for other scheduling algorithms
        for job in jobs:
            job.reset_processing()

        # Create a list of jobs by sorted arrival time
        MLFQjobs = []
        for job in jobs:
            MLFQjobs.append(JobWithEstimate(job))
        MLFQjobs.sort(key=lambda j: j.arrival)

        # Perform Balanced MLFQ scheduling
        schedule, Balanced_MLFQ_total_flow_time = Balanced_MLFQ(MLFQjobs)
        average_balanced_mlfq_flow_time += Balanced_MLFQ_total_flow_time/num_runs
        max_balanced_mlfq_flow_time = max(max_balanced_mlfq_flow_time, Balanced_MLFQ_total_flow_time)

        num_times_balanced_mlfq_better += 1 if Balanced_MLFQ_total_flow_time < MLFQ_total_flow_time else 0

    print(f"\nMinimum job length: {MIN_LENGTH}, Maximum job length: {MAX_LENGTH}")
    print(f"Minimum arrival time: {MIN_ARRIVAL}, Maximum arrival time: {MAX_ARRIVAL}")
    print(f"Number of jobs: {NUM_JOBS}, Number of runs: {num_runs}")

    print(f"\nmu1: {MU1}, mu2: {MU2}, e: {E}")

    print(f"\nAverage flow times:")
    print(f"SRPT: {average_srpt_flow_time}")
    print(f"MLFQ: {average_mlfq_flow_time}")
    print(f"Balanced MLFQ: {average_balanced_mlfq_flow_time}")

    print(f"\nMaximum flow times:")
    print(f"SRPT: {max_srpt_flow_time}")
    print(f"MLFQ: {max_mlfq_flow_time}")
    print(f"Balanced MLFQ: {max_balanced_mlfq_flow_time}")

    print(f"\nNumber of times Balanced MLFQ was better: {num_times_balanced_mlfq_better}")
    

if __name__ == "__main__":
    full_test()