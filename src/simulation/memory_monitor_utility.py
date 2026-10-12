import time
import os
import psutil
import torch

class MemoryMonitorUtility:
    """
    Utility for real-time memory and system performance monitoring:
    - Process RAM RSS (MB) & Peak Memory
    - PyTorch GPU/CPU Neural Memory consumption
    - Entity Object Pool statistics
    - Simulation Tick Latencies (ms) and Frames Per Second (FPS)
    """
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0.0
        self.tick_times = []

    def record_tick_time(self, elapsed_sec):
        self.tick_times.append(elapsed_sec)
        if len(self.tick_times) > 100:
            self.tick_times.pop(0)

    def update_fps(self):
        self.frame_count += 1
        now = time.time()
        delta = now - self.last_time
        if delta >= 1.0:
            self.fps = self.frame_count / delta
            self.frame_count = 0
            self.last_time = now

    def get_memory_stats(self, entity_factory=None):
        mem_info = self.process.memory_info()
        rss_mb = mem_info.rss / (1024 * 1024)
        vsz_mb = mem_info.vms / (1024 * 1024)

        stats = {
            "ram_rss_mb": round(rss_mb, 2),
            "ram_vsz_mb": round(vsz_mb, 2),
            "cpu_percent": round(self.process.cpu_percent(), 1),
            "fps": round(self.fps, 1),
            "avg_tick_ms": round((sum(self.tick_times) / len(self.tick_times) * 1000) if self.tick_times else 0.0, 2),
        }

        if torch.cuda.is_available():
            stats["gpu_allocated_mb"] = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
            stats["gpu_reserved_mb"] = round(torch.cuda.memory_reserved() / (1024 * 1024), 2)
        else:
            stats["gpu_allocated_mb"] = 0.0
            stats["gpu_reserved_mb"] = 0.0

        if entity_factory:
            stats["pools"] = entity_factory.get_pool_stats()

        return stats

    def format_summary(self, entity_factory=None):
        m = self.get_memory_stats(entity_factory)
        summary = f"RAM: {m['ram_rss_mb']} MB | CPU: {m['cpu_percent']}% | FPS: {m['fps']} | Avg Tick: {m['avg_tick_ms']} ms"
        if m['gpu_allocated_mb'] > 0:
            summary += f" | GPU Alloc: {m['gpu_allocated_mb']} MB"
        if "pools" in m:
            summary += f" | Pooled Z:{m['pools']['zombies_pooled']} S:{m['pools']['scents_pooled']} N:{m['pools']['noises_pooled']}"
        return summary
