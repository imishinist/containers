import { Cluster } from "ioredis";
import Redlock from "redlock";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const LOCK_TTL = 5000 /* ms */;
const key = "my_key";

(async function() {
  let redis;
  try {
    redis = new Cluster([
      { host: "localhost", port: 7001 },
      { host: "localhost", port: 7002 },
      { host: "localhost", port: 7003 },
    ]);
  } catch (err) {
    console.error(err);
  }
  redis.on("error", console.error);
  const redlock = new Redlock([redis], {
    driftFactor: 0.01,
    retryCount: 10,
    retryDelay: 200,
    retryJitter: 200,
  });

  let lock;
  try {
    lock = await redlock.lock(key, LOCK_TTL);
    console.log(lock);
    await sleep(5200)
  } catch (error) {
    console.error(error);
  } finally {
    if (lock) {
      console.log(await lock.unlock());
    }
    await redlock.quit();
    await redis.quit();
  }
})();

