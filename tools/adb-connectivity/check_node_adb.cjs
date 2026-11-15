'use strict';

// JSON output is consumed by test_connectivity.py.
const watchdog = setTimeout(() => {
  console.error('Node.js ADB checks timed out after 60 seconds.');
  process.exit(1);
}, 60000);

async function main() {
  const adb = require('@devicefarmer/adbkit').default;
  const client = adb.createClient({ host: '127.0.0.1', port: 5037 });
  const serverVersion = await client.version();
  const devices = await client.listDevices();
  const results = [];

  for (const info of devices) {
    const result = { serial: info.id, state: info.type, ok: false };
    if (info.type === 'device') {
      try {
        const device = client.getDevice(info.id);
        const stream = await device.shell('echo adb_connection_ok');
        const response = (await adb.util.readAll(stream)).toString('utf8').trim();
        if (response !== 'adb_connection_ok') {
          throw new Error(`Unexpected shell response: ${JSON.stringify(response)}`);
        }
        result.ok = true;
      } catch (error) {
        result.error = error.message;
      }
    } else {
      result.error = 'Device is not authorized or ready.';
    }
    results.push(result);
  }

  console.log(JSON.stringify({ serverVersion, devices: results }));
}

main().then(
  () => clearTimeout(watchdog),
  (error) => {
    clearTimeout(watchdog);
    console.error(error.message);
    process.exitCode = 1;
  },
);
