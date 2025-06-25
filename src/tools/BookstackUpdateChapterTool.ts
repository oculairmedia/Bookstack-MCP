import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";

interface Tag {
  name: string;
  value: string;
}

interface UpdateChapterInput {
  id: string;
  book_id?: string;
  name?: string;
  description?: string;
  tags?: Tag[];
  priority?: string;
}

class BookstackUpdateChapterTool extends MCPTool<UpdateChapterInput> {
  name = "bookstack_update_chapter";
  description = "Updates a chapter in Bookstack";
  toolBase = new BookstackToolBase();

  schema = {
    id: {
      type: z.string(),
      description: "The ID of the chapter to update",
    },
    book_id: {
      type: z.string().optional(),
      description: "The ID of the book to move the chapter to",
    },
    name: {
      type: z.string().optional(),
      description: "The new name of the chapter",
    },
    description: {
      type: z.string().optional(),
      description: "A new description of the chapter",
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
    priority: {
      type: z.string().optional(),
      description: "New chapter priority",
    },
  };

  async execute(input: UpdateChapterInput) {
    try {
      console.log(`Executing bookstack_update_chapter with input: ${JSON.stringify(input)}`);
      
      // Convert string inputs to numbers
      const id = parseInt(input.id, 10);
      const book_id = input.book_id ? parseInt(input.book_id, 10) : undefined;
      const priority = input.priority ? parseInt(input.priority, 10) : undefined;
      
      // Validate converted numbers
      if (isNaN(id) || id <= 0) {
        return `Error: Invalid id value. Must be a positive number.`;
      }
      
      if (input.book_id && (isNaN(book_id!) || book_id! <= 0)) {
        return `Error: Invalid book_id value. Must be a positive number.`;
      }
      
      if (input.priority && isNaN(priority!)) {
        return `Error: Invalid priority value. Must be a number.`;
      }
      
      // Ensure at least one field to update is provided
      if (!input.book_id && !input.name && !input.description && !input.tags && !input.priority) {
        return `Error: At least one field to update must be provided.`;
      }
      
      const result = await this.toolBase.executePythonScript("update_chapter", {
        id: id,
        book_id: book_id,
        name: input.name,
        description: input.description,
        tags: input.tags,
        priority: priority
      });
      
      // Return the result as a string
      return result;
    } catch (error: any) {
      console.error("Error executing bookstack_update_chapter:", error);
      return `Error: ${error.message || 'Unknown error'}`;
    }
  }
}

export default BookstackUpdateChapterTool;