import { MCPTool } from "mcp-framework";
import { z } from "zod";
interface ExampleToolInput {
    message: string;
}
declare class ExampleToolTool extends MCPTool<ExampleToolInput> {
    name: string;
    description: string;
    schema: {
        message: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: ExampleToolInput): Promise<string>;
}
export default ExampleToolTool;
