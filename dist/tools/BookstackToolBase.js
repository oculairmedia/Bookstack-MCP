import { spawn } from "child_process";
import * as path from "path";
/**
 * Base class for Bookstack tools that provides common functionality
 */
export class BookstackToolBase {
    /**
     * Executes a Python script with the given script name and arguments
     *
     * @param scriptName The name of the Python script to execute (without .py extension)
     * @param args The arguments to pass to the Python script as a dictionary
     * @returns A promise that resolves to the output of the Python script
     */
    async executePythonScript(scriptName, args) {
        return new Promise((resolve, reject) => {
            try {
                // Convert arguments to Python code
                const argStrings = [];
                for (const [key, value] of Object.entries(args)) {
                    let pythonValue;
                    if (value === undefined || value === null) {
                        pythonValue = 'None';
                    }
                    else if (typeof value === 'string') {
                        // Escape triple quotes in strings
                        const escapedValue = value.replace(/"""/g, '\\"\\"\\"');
                        pythonValue = `"""${escapedValue}"""`;
                    }
                    else if (typeof value === 'number' || typeof value === 'boolean') {
                        pythonValue = String(value);
                    }
                    else if (Array.isArray(value)) {
                        pythonValue = JSON.stringify(value);
                    }
                    else if (typeof value === 'object') {
                        pythonValue = JSON.stringify(value);
                    }
                    else {
                        pythonValue = 'None';
                    }
                    argStrings.push(`${key} = ${pythonValue}`);
                }
                // Determine script paths
                const srcToolsPath = path.resolve(process.cwd(), 'src/tools');
                const distToolsPath = path.resolve(process.cwd(), 'dist/tools');
                console.log(`Looking for ${scriptName}.py in:`, srcToolsPath, distToolsPath);
                // Prepare Python code to execute
                const pythonCode = `
import sys
# Add both possible script locations to Python path
sys.path.append("${srcToolsPath.replace(/\\/g, '/')}")
sys.path.append("${distToolsPath.replace(/\\/g, '/')}")
import json
from '${scriptName}' import '${scriptName}'


# Parse input arguments
${argStrings.join('\n')}

# Call the function
result = '${scriptName}'(${Object.keys(args).join(', ')})

# Format response as JSON-RPC
response = {
    "jsonrpc": "2.0",
    "method": "${scriptName}",  # Add method name
    "id": 1,  # Fixed ID since we don't receive one from the tool call
    "params": args,  # Add params
    "result": {
        "type": "success",
        "data": json.loads(result) if isinstance(result, str) else result,
        "content": [{
            "type": "text",
            "text": json.dumps({
                "success": True,
                "data": json.loads(result) if isinstance(result, str) else result
            }, indent=2)
        }]
    }
}

# Handle errors
try:
    json.dumps(response)
except Exception as e:
    response = {
        "jsonrpc": "2.0",
        "method": "${scriptName}",
        "id": 1,
        "params": args,
        "error": {
            "code": -32000,
            "message": str(e),
            "data": {
                "type": "error",
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                }]
            }
        }
    }
print(json.dumps(response))
        `;
                // Spawn Python process
                const pythonProcess = spawn("python", ["-c", pythonCode]);
                let stdout = "";
                let stderr = "";
                // Collect stdout
                pythonProcess.stdout.on("data", (data) => {
                    stdout += data.toString();
                });
                // Collect stderr
                pythonProcess.stderr.on("data", (data) => {
                    stderr += data.toString();
                });
                // Handle process completion
                pythonProcess.on("close", (code) => {
                    if (code !== 0) {
                        console.error(`Python process exited with code ${code}`);
                        console.error(`stderr: ${stderr}`);
                        reject(`Error: Python process exited with code ${code}. ${stderr}`);
                    }
                    else {
                        try {
                            // Parse JSON response from Python
                            const trimmedOutput = stdout.trim();
                            const result = JSON.parse(trimmedOutput);
                            resolve(JSON.stringify(result));
                        }
                        catch (error) {
                            console.error(`Error parsing Python output as JSON: ${stdout}`);
                            reject(`Error parsing Python output as JSON: ${error}`);
                        }
                    }
                });
            }
            catch (error) {
                console.error(`Exception executing ${scriptName}.py: ${error}`);
                reject(`Error: ${error}`);
            }
        });
    }
}
// Export the class as default export
