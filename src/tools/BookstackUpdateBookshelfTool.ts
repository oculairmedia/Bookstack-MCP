import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface Tag {
  name: string;
  value: string;
}

interface UpdateBookshelfInput {
  id: string;
  name?: string;
  description?: string;
  books?: string[];
  tags?: Tag[];
}

class BookstackUpdateBookshelfTool extends MCPTool<UpdateBookshelfInput> {
  name = "bookstack_update_bookshelf";
  description = "Updates a bookshelf in Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    id: {
      type: z.string(),
      description: "The ID of the bookshelf to update",
    },
    name: {
      type: z.string().optional(),
      description: "The new name of the bookshelf",
    },
    description: {
      type: z.string().optional(),
      description: "A new description of the bookshelf",
    },
    books: {
      type: z.array(z.string()).optional(),
      description: "A new list of book IDs to include in the shelf",
    },
    tags: {
      type: z.array(
        z.object({
          name: z.string(),
          value: z.string(),
        })
      ).optional(),
      description: "A new list of tag objects (each with 'name' and 'value')",
    },
  };

  async execute(input: UpdateBookshelfInput) {
    try {
      console.log(`Executing bookstack_update_bookshelf with input: ${JSON.stringify(input)}`);
      
      // Convert string id to number
      const id = parseInt(input.id, 10);
      
      // Validate converted number
      if (isNaN(id) || id <= 0) {
        return `Error: Invalid id value. Must be a positive number.`;
      }
      
      // Convert string book IDs to numbers if provided
      let bookIds: number[] | undefined;
      if (input.books && input.books.length > 0) {
        bookIds = input.books.map(id => {
          const numId = parseInt(id, 10);
          if (isNaN(numId)) {
            throw new Error(`Invalid book ID: ${id}. Must be a number.`);
          }
          return numId;
        });
      }
      
      // Ensure at least one field to update is provided
      if (!input.name && !input.description && !input.books && !input.tags) {
        return `Error: At least one field to update must be provided.`;
      }
      
      const result = await this.toolBase.executePythonScript("update_bookshelf", {
        id: id,
        name: input.name,
        description: input.description,
        books: bookIds,
        tags: input.tags
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_update_bookshelf:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackUpdateBookshelfTool;