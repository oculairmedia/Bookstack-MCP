import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface Tag {
  name: string;
  value: string;
}

interface CreateBookInput {
  name: string;
  description: string;
  tags?: Tag[];
  image_id?: string;
}

class BookstackCreateBookTool extends MCPTool<CreateBookInput> {
  name = "bookstack_create_book";
  description = "Creates a new book in Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    name: {
      type: z.string(),
      description: "The name of the book",
    },
    description: {
      type: z.string(),
      description: "A description of the book",
    },
    tags: {
      type: z.array(
        z.object({
          name: z.string(),
          value: z.string(),
        })
      ).optional(),
      description: "A list of tag objects (each with 'name' and 'value')",
    },
    image_id: {
      type: z.string().optional(),
      description: "The ID of an image to use as the cover",
    },
  };

  async execute(input: CreateBookInput) {
    try {
      console.log(`Executing bookstack_create_book with input: ${JSON.stringify(input)}`);
      
      // Convert string input to number
      const image_id = input.image_id ? parseInt(input.image_id, 10) : undefined;
      
      // Validate converted number
      if (input.image_id && isNaN(image_id!)) {
        return `Error: Invalid image_id value. Must be a number.`;
      }
      
      const result = await this.toolBase.executePythonScript("create_book", {
        name: input.name,
        description: input.description,
        tags: input.tags,
        image_id: image_id
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_create_book:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

// Export the class
export default BookstackCreateBookTool;