import random

random.seed(1)


def line(g, status="OK", countdown=0, steps=0):
    p = [random.randint(50, 300) for _ in range(4)]
    return (f"F:{g:.2f},T:{random.uniform(30, 32):.1f},"
            f"P1:{p[0]},P2:{p[1]},P3:{p[2]},P4:{p[3]},"
            f"C:{countdown},S:{status},ST:{steps}\n")


# Session A: walk, real fall, lie still, countdown, SOS
with open("fake_fall.txt", "w") as f:
    for i in range(10):
        f.write(line(random.uniform(0.6, 1.6), steps=i))
    f.write(">> Impact detected\n")
    f.write(line(3.1, steps=10))
    for _ in range(6):
        f.write(line(1.0, steps=10))
    f.write("!!! FALL DETECTED !!!\n")
    for c in range(10, 0, -2):
        f.write(line(1.0, status="FALL", countdown=c, steps=10))
    f.write("*** SENDING SOS ***\n")

# Session B: walking, stumble, false alarm, cancelled from app
with open("fake_walk.txt", "w") as f:
    for i in range(10):
        f.write(line(random.uniform(0.6, 1.6), steps=i))
    f.write(">> Impact detected\n")
    f.write(line(2.8, steps=10))
    for _ in range(6):
        f.write(line(1.0, steps=10))
    f.write("!!! FALL DETECTED !!!\n")
    f.write(line(1.0, status="FALL", countdown=10, steps=10))
    f.write(">> Alert cancelled from app\n")
    for i in range(10):
        f.write(line(random.uniform(0.6, 1.6), steps=11 + i))

print("Wrote fake_fall.txt and fake_walk.txt")