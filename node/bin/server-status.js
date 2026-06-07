#!/usr/bin/env node
const { listServerProcesses, printServerProcesses } = require("./server-processes");

const processes = listServerProcesses();
if (processes.length === 0) {
  console.log("No active bank-api Node server found.");
  process.exit(1);
}

console.log("Active bank-api Node server process" + (processes.length === 1 ? "" : "es") + ":");
printServerProcesses(processes);
