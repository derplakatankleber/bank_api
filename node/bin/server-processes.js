const { execFileSync } = require("node:child_process");
const path = require("node:path");

const SERVER_SCRIPT = path.resolve(__dirname, "../src/api/app.js");
const SERVER_SCRIPT_RELATIVE = path.join("node", "src", "api", "app.js");

function listServerProcesses() {
  const output = execFileSync("ps", ["-eo", "pid=,ppid=,command="], { encoding: "utf8" });
  return output
    .split("\n")
    .map(parseProcessLine)
    .filter(Boolean)
    .filter(isBankApiServerProcess);
}

function parseProcessLine(line) {
  const match = line.trim().match(/^(\d+)\s+(\d+)\s+(.+)$/);
  if (!match) {
    return null;
  }
  return {
    pid: Number(match[1]),
    ppid: Number(match[2]),
    command: match[3]
  };
}

function isBankApiServerProcess(processInfo) {
  const command = processInfo.command;
  if (!isNodeCommand(command)) {
    return false;
  }
  return command.includes(SERVER_SCRIPT) || command.includes(SERVER_SCRIPT_RELATIVE);
}

function isNodeCommand(command) {
  return /^node(\s|$)/.test(command) || /^\S+\/node(\s|$)/.test(command);
}

function printServerProcesses(processes) {
  console.log("PID\tPPID\tCOMMAND");
  for (const processInfo of processes) {
    console.log(String(processInfo.pid) + "\t" + String(processInfo.ppid) + "\t" + processInfo.command);
  }
}

module.exports = {
  listServerProcesses,
  printServerProcesses
};
