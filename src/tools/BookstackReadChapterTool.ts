import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface ReadChapterInput {
  id: string;
}

class BookstackReadChapterTool extends MCPTool<ReadChapterInput> {
  name = "bookstack_read_chapter";
  description = "Retrieves details of a specific chapter in Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    id: {
      type: z.string(),
      description: "The ID of the chapter to retrieve",
    },
  };

  async execute(input: ReadChapterInput) {
    try {
      console.log(`Executing bookstack_read_chapter with input: ${JSON.stringify(input)}`);
      
      // Convert string input to number
      const id = parseInt(input.id, 10);
      
      // Validate converted number
      if (isNaN(id) || id <= 0) {
        return `Error: Invalid id value. Must be a positive number.`;
      }
      
      const result = await this.toolBase.executePythonScript("read_chapter", {
        id: id
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_read_chapter:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackReadChapterTool;