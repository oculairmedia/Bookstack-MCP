import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type CreatePageInput = z.infer<typeof schema>;
declare class BookstackCreatePageTool extends BookstackTool<CreatePageInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: CreatePageInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreatePageTool;
