#!/usr/bin/env node
const { listServerProcesses, printServerProcesses } = require("./server-processes");

const processes = listServerProcesses();
if (processes.length === 0) {
  console.log("No active bank-api Node server found.");
  process.exit(0);
}

console.log("Stopping bank-api Node server process" + (processes.length === 1 ? "" : "es") + ":");
printServerProcesses(processes);

for (const processInfo of processes) {
  try {
    process.kill(processInfo.pid, "SIGTERM");
  } catch (error) {
    if (error.code !== "ESRCH") {
      console.error("Failed to stop PID " + processInfo.pid + ": " + error.message);
    }
  }
}

setTimeout(() => {
  const stillRunning = listServerProcesses().filter((processInfo) => {
    return processes.some((stopped) => stopped.pid === processInfo.pid);
  });
  if (stillRunning.length > 0) {
    console.error("Some bank-api Node server processes are still running:");
    printServerProcesses(stillRunning);
    process.exit(1);
  }
  console.log("Stopped bank-api Node server.");
}, 500);
