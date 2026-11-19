import random as r

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

    # Zero-length jobs have no processing time and finish upon arrival.
    for job in jobs:
        if job.length == 0:
            completion_times[job] = job.arrival

    # Calculate total flow time for comparison with other scheduling algorithms
    total_flow_time = sum(completion_times[job] - job.arrival for job in jobs)
    return schedule, total_flow_time

# Multilevel Feedback Queue Implementation
# Default quantums are set to 2, 4, 8, and 16 for the first four queues, with the last queue being FCFS.
def MLFQ(jobs, quantums=(2, 4, 8, 16), queue_count=5):
    if queue_count < 1:
        raise ValueError("queue_count must be at least 1")
    if len(quantums) != queue_count - 1:
        raise ValueError("provide one quantum for each transitionable queue")

    queues = [[] for _ in range(queue_count)]
    remaining_quantums = {}
    completion_times = {}
    schedule = []
    time = 0

    while any(not job.is_complete() for job in jobs):
        for job in jobs:
            #add new jobs to the first queue when they arrive
            if job.arrival == time:
                queues[0].append(job)
                remaining_quantums[job] = quantums[0]

        # Select the first non-empty queue
        selected_queue = None
        for queue in queues:
            if len(queue) > 0:
                selected_queue = queues.index(queue)
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

        if job.is_complete():
            completion_times[job] = time + 1
        # Move the job back to the last queue if it is the last queue
        elif selected_queue == queue_count - 1:
            queues[selected_queue].append(job)
        # Move the job to the next queue if it has used up its quantum
        else:
            remaining_quantums[job] -= 1
            if remaining_quantums[job] == 0:
                next_queue = selected_queue + 1
                queues[next_queue].append(job)
                if next_queue < len(quantums):
                    remaining_quantums[job] = quantums[next_queue]
            else:
                queues[selected_queue].append(job)

        time += 1

    # Zero-length jobs finish when they arrive.
    for job in jobs:
        if job.length == 0:
            completion_times[job] = job.arrival

    total_flow_time = sum(completion_times[job] - job.arrival for job in jobs)
    return schedule, total_flow_time


if __name__ == "__main__":
    
    # Set seed
    r.seed(0)

    # Create a list of jobs by sorted time
    jobs = []
    for x in range(10):
        jobs.append(Job(r.randint(0, 40), r.randint(1, 10)))
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
