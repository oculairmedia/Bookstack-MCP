/**
 * Base class for Bookstack tools that provides common functionality
 */
export declare class BookstackToolBase {
    /**
     * Executes a Python script with the given script name and arguments
     *
     * @param scriptName The name of the Python script to execute (without .py extension)
     * @param args The arguments to pass to the Python script as a dictionary
     * @returns A promise that resolves to the output of the Python script
     */
    executePythonScript(scriptName: string, args: Record<string, any>): Promise<string>;
}
