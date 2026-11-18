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
        available_jobs = [job for job in jobs if job.arrival <= time and not job.is_complete()] 

        if available_jobs:
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

    total_flow_time = sum(completion_times[job] - job.arrival for job in jobs)
    return schedule, total_flow_time


if __name__ == "__main__":
    
    # Set seed
    r.seed(0)

    # Create a list of jobs by sorted time
    jobs = []
    for x in range(10):
        jobs.append(Job(r.randint(0, 20), r.randint(0, 10)))
    jobs.sort(key=lambda j: j.arrival)

    # Print the list of jobs
    print("\n".join(f"Job {jobs.index(job)}: {str(job)}" for job in jobs))

    #perform SRPT scheduling
    schedule, total_flow_time = SRPT(jobs)
    print("\nSRPT schedule:")
    for time, job_index in schedule:
        if job_index is None:
            print(f"Time {time}: idle")
        else:
            print(f"Time {time}: job {job_index}")
    print(f"Total flow time: {total_flow_time}")
    for job in jobs:
        job.reset_processing()  # Reset processing for other scheduling algorithms
