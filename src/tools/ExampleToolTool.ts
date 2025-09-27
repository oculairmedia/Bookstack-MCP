import { MCPTool } from "mcp-framework";
import { z } from "zod";

interface ExampleToolInput {
  message: string;
}

class ExampleToolTool extends MCPTool<ExampleToolInput> {
  name = "example_tool_duplicate";
  description = "An example tool that processes messages";

  schema = {
    message: {
      type: z.string(),
      description: "Message to process",
    },
  };

  async execute(input: ExampleToolInput) {
    return `Processed: ${input.message}`;
  }
}

export default ExampleToolTool;