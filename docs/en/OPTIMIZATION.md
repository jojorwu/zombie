# Neural Networks & Optimizations

## Batched Neural Inference
- `BrainNet` processes all active survivors in a single batched PyTorch forward pass, drastically reducing CPU/GPU call overhead.
- GRU recurrent neural network hidden states (`h_next`) maintain memory of past environmental stimuli.

## Memory Management & Chunking
- `ChunkManager` handles spatial partitioning of 16x16 map chunks.
- Active chunks are dynamically loaded/unloaded based on entity view distances and camera viewports.
- Garbage collection (`gc.collect()`) and PyTorch CUDA cache clearing occur seamlessly on generation resets to eliminate memory leaks.
