import { MCPTool } from "mcp-framework";
import { z } from "zod";
interface ExampleInput {
    message: string;
}
declare class ExampleTool extends MCPTool<ExampleInput> {
    name: string;
    description: string;
    schema: {
        message: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: ExampleInput): Promise<string>;
}
export default ExampleTool;
