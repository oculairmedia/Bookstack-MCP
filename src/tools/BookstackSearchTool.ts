import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface BookstackSearchToolInput {
  query: string;
  page?: string;
  count?: string;
}

class BookstackSearchTool extends MCPTool<BookstackSearchToolInput> {
  name = "bookstack_search";
  description = "Searches content (shelves, books, chapters, pages) in BookStack. Uses advanced search syntax.";
  toolBase = new BookstackToolBase();

  schema = {
    query: {
      type: z.string(),
      description: "The search query string. Supports advanced BookStack search syntax.",
    },
    page: {
      type: z.string().optional(),
      description: "The page number for pagination.",
    },
    count: {
      type: z.string().optional(),
      description: "The number of results per page (max 100).",
    },
  };

  async execute(input: BookstackSearchToolInput) {
    try {
      console.log(`Executing bookstack_search with input: ${JSON.stringify(input)}`);
      
      // Convert string inputs to numbers where needed
      const page = input.page ? parseInt(input.page, 10) : undefined;
      const count = input.count ? parseInt(input.count, 10) : undefined;
      
      // Validate converted numbers
      if (page !== undefined && (isNaN(page) || page < 1)) {
        return `Error: Invalid page value. Must be a positive number.`;
      }
      
      if (count !== undefined && (isNaN(count) || count < 1 || count > 100)) {
        return `Error: Invalid count value. Must be a positive number (max 100).`;
      }
      
      const scriptArgs = {
        query: input.query,
        ...(page && { page: page }),
        ...(count && { count: count }),
      };

      const result = await this.toolBase.executePythonScript("search", scriptArgs);
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_search:", error);
      // Return the full error message which includes Python traceback details
      return `Error: ${error.message || error || 'Unknown error'}`;
    }
  }
}

export default BookstackSearchTool;