import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface ListBookshelvesInput {
  offset?: string;
  count?: string;
}

class BookstackListBookshelvesTool extends MCPTool<ListBookshelvesInput> {
  name = "bookstack_list_bookshelves";
  description = "Lists all bookshelves in Bookstack with pagination support";
  toolBase = new BookstackToolBase();

  schema = {
    offset: {
      type: z.string().optional(),
      description: "Number of records to skip",
    },
    count: {
      type: z.string().optional(),
      description: "Number of records to take",
    },
  };

  async execute(input: ListBookshelvesInput) {
    try {
      console.log(`Executing bookstack_list_bookshelves with input: ${JSON.stringify(input)}`);
      
      // Convert string inputs to numbers
      const offset = input.offset ? parseInt(input.offset, 10) : 0;
      const count = input.count ? parseInt(input.count, 10) : 100;
      
      // Validate converted numbers
      if (isNaN(offset) || offset < 0) {
        return `Error: Invalid offset value. Must be a non-negative number.`;
      }
      
      if (isNaN(count) || count <= 0) {
        return `Error: Invalid count value. Must be a positive number.`;
      }
      
      const result = await this.toolBase.executePythonScript("list_bookshelves", {
        offset: offset,
        count: count
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_list_bookshelves:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackListBookshelvesTool;