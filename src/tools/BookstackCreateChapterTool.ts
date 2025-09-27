import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface Tag {
  name: string;
  value: string;
}

interface CreateChapterInput {
  book_id: string;
  name: string;
  description?: string;
  tags?: Tag[];
  priority?: string;
}

class BookstackCreateChapterTool extends MCPTool<CreateChapterInput> {
  name = "bookstack_create_chapter";
  description = "Creates a new chapter in Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    book_id: {
      type: z.string(),
      description: "The ID of the book to create the chapter in",
    },
    name: {
      type: z.string(),
      description: "The name of the chapter",
    },
    description: {
      type: z.string().optional(),
      description: "A description of the chapter",
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
    priority: {
      type: z.string().optional(),
      description: "Chapter priority",
    },
  };

  async execute(input: CreateChapterInput) {
    try {
      console.log(`Executing bookstack_create_chapter with input: ${JSON.stringify(input)}`);
      
      // Convert string inputs to numbers
      const book_id = parseInt(input.book_id, 10);
      const priority = input.priority ? parseInt(input.priority, 10) : undefined;
      
      // Validate converted numbers
      if (isNaN(book_id) || book_id <= 0) {
        return `Error: Invalid book_id value. Must be a positive number.`;
      }
      
      if (input.priority && isNaN(priority!)) {
        return `Error: Invalid priority value. Must be a number.`;
      }
      
      const result = await this.toolBase.executePythonScript("create_chapter", {
        book_id: book_id,
        name: input.name,
        description: input.description,
        tags: input.tags,
        priority: priority
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_create_chapter:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackCreateChapterTool;