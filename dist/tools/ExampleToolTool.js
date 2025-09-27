import { MCPTool } from "mcp-framework";
import { z } from "zod";
class ExampleToolTool extends MCPTool {
    constructor() {
        super(...arguments);
        this.name = "example_tool_duplicate";
        this.description = "An example tool that processes messages";
        this.schema = {
            message: {
                type: z.string(),
                description: "Message to process",
            },
        };
    }
    async execute(input) {
        return `Processed: ${input.message}`;
    }
}
export default ExampleToolTool;
