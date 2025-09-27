import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface DeletePageInput {
  id: string;
}

class BookstackDeletePageTool extends MCPTool<DeletePageInput> {
  name = "bookstack_delete_page";
  description = "Deletes a page from Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    id: {
      type: z.string(),
      description: "The ID of the page to delete",
    },
  };

  async execute(input: DeletePageInput) {
    try {
      console.log(`Executing bookstack_delete_page with input: ${JSON.stringify(input)}`);
      
      // Convert string input to number
      const id = parseInt(input.id, 10);
      
      // Validate converted number
      if (isNaN(id) || id <= 0) {
        return `Error: Invalid id value. Must be a positive number.`;
      }
      
      const result = await this.toolBase.executePythonScript("delete_page", {
        id: id
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_delete_page:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackDeletePageTool;