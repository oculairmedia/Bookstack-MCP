import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface ReadPageInput {
  id: string;
}

class BookstackReadPageTool extends MCPTool<ReadPageInput> {
  name = "bookstack_read_page";
  description = "Retrieves details of a specific page in Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    id: {
      type: z.string(),
      description: "The ID of the page to retrieve",
    },
  };

  async execute(input: ReadPageInput) {
    try {
      console.log(`Executing bookstack_read_page with input: ${JSON.stringify(input)}`);
      
      // Convert string input to number
      const id = parseInt(input.id, 10);
      
      // Validate converted number
      if (isNaN(id) || id <= 0) {
        return `Error: Invalid id value. Must be a positive number.`;
      }
      
      const result = await this.toolBase.executePythonScript("read_page", {
        id: id
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_read_page:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackReadPageTool;