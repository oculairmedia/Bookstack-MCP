import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface Tag {
  name: string;
  value: string;
}

interface UpdateBookInput {
  id: string;
  name?: string;
  description?: string;
  tags?: Tag[];
  image_id?: string;
}

class BookstackUpdateBookTool extends MCPTool<UpdateBookInput> {
  name = "bookstack_update_book";
  description = "Updates a book in Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    id: {
      type: z.string(),
      description: "The ID of the book to update",
    },
    name: {
      type: z.string().optional(),
      description: "The new name of the book",
    },
    description: {
      type: z.string().optional(),
      description: "A new description of the book",
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
    image_id: {
      type: z.string().optional(),
      description: "The ID of a new image to use as the cover",
    },
  };

  async execute(input: UpdateBookInput) {
    try {
      console.log(`Executing bookstack_update_book with input: ${JSON.stringify(input)}`);
      
      // Convert string inputs to numbers
      const id = parseInt(input.id, 10);
      const image_id = input.image_id ? parseInt(input.image_id, 10) : undefined;
      
      // Validate converted numbers
      if (isNaN(id) || id <= 0) {
        return `Error: Invalid id value. Must be a positive number.`;
      }
      
      if (input.image_id && isNaN(image_id!)) {
        return `Error: Invalid image_id value. Must be a number.`;
      }
      
      // Ensure at least one field to update is provided
      if (!input.name && !input.description && !input.tags && !input.image_id) {
        return `Error: At least one field to update must be provided.`;
      }
      
      const result = await this.toolBase.executePythonScript("update_book", {
        id: id,
        name: input.name,
        description: input.description,
        tags: input.tags,
        image_id: image_id
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_update_book:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackUpdateBookTool;