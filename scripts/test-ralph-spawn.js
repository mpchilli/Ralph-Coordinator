import { spawn } from 'child_process';
import path from 'path';
import os from 'os';

async function testRalphSpawn() {
    const repoRoot = process.cwd();
    const ralphCmd = path.join(repoRoot, 'ralph.cmd');

    console.log(`Testing spawn of ${ralphCmd}...`);

    return new Promise((resolve, reject) => {
        const isWin = os.platform() === 'win32';
        const command = isWin ? `"${ralphCmd}"` : ralphCmd;

        // Test 1: Spawn bridge --version
        const proc = spawn(command, ['--version'], {
            shell: isWin,
            stdio: 'pipe'
        });

        let output = '';
        proc.stdout.on('data', (data) => {
            output += data.toString();
        });

        proc.on('close', (code) => {
            if (code === 0 && output.includes('ralph-coordinator')) {
                console.log('✅ Spawn test passed!');
                console.log(`Version output: ${output.trim()}`);
                resolve(true);
            } else {
                console.error(`❌ Spawn test failed with code ${code}`);
                console.error(`Output: ${output}`);
                reject(new Error('Spawn failed'));
            }
        });

        proc.on('error', (err) => {
            console.error('❌ Spawn error:', err);
            reject(err);
        });
    });
}

testRalphSpawn().catch(err => {
    console.error(err);
    process.exit(1);
});
