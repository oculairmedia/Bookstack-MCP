import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface ListBooksInput {
  offset?: string;
  count?: string;
}

class BookstackListBooksTool extends MCPTool<ListBooksInput> {
  name = "bookstack_list_books";
  description = "Lists all books in Bookstack with pagination support";
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

  async execute(input: ListBooksInput) {
    try {
      console.log(`Executing bookstack_list_books with input: ${JSON.stringify(input)}`);
      
      // Convert string inputs to numbers
      const offset = input.offset ? parseInt(input.offset, 10) : 0;
      const count = input.count ? parseInt(input.count, 10) : 100;
      
      // Validate converted numbers
      if (isNaN(offset) || offset < 0) {
        throw new Error('Invalid offset value. Must be a non-negative number.');
      }
      
      if (isNaN(count) || count <= 0) {
        throw new Error('Invalid count value. Must be a positive number.');
      }
      
      const result = await this.toolBase.executePythonScript("list_books", {
        offset: offset,
        count: count
      });

      // The result from Python is already a properly formatted JSON-RPC response
      // Just parse and return it
      const parsedResult = JSON.parse(result);
      
      // Format the response according to MCP framework expectations
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(parsedResult, null, 2)
          }
        ]
      };
      
      // return parsedResult;
    } catch (error: any) {
      // If the error comes from Python, it will be in the result JSON
      if (error.message && error.message.includes('JSON')) {
        console.error("Error executing bookstack_list_books:", error);
        
        return {
          jsonrpc: "2.0",
          method: "list_books",
          id: 1,
          params: {
            offset: input.offset,
            count: input.count
          },
          error: {
            code: -32000,
            message: error.message || 'Unknown error',
            data: {
              type: "error",
              content: [{
                type: "text",
                text: JSON.stringify({
                  success: false,
                  error: error.message || 'Unknown error'
                }, null, 2)
              }]
            }
          }
        };
      }
      
      // If it's a Python error, it will already be properly formatted
      throw error;
    }
  }
}

export default BookstackListBooksTool;