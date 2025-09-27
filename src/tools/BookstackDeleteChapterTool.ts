import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface DeleteChapterInput {
  id: string;
}

class BookstackDeleteChapterTool extends MCPTool<DeleteChapterInput> {
  name = "bookstack_delete_chapter";
  description = "Deletes a chapter from Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    id: {
      type: z.string(),
      description: "The ID of the chapter to delete",
    },
  };

  async execute(input: DeleteChapterInput) {
    try {
      console.log(`Executing bookstack_delete_chapter with input: ${JSON.stringify(input)}`);
      
      // Convert string input to number
      const id = parseInt(input.id, 10);
      
      // Validate converted number
      if (isNaN(id) || id <= 0) {
        return `Error: Invalid id value. Must be a positive number.`;
      }
      
      const result = await this.toolBase.executePythonScript("delete_chapter", {
        id: id
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_delete_chapter:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackDeleteChapterTool;