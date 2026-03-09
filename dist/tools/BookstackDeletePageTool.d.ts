import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type DeletePageInput = z.infer<typeof schema>;
declare class BookstackDeletePageTool extends BookstackTool<DeletePageInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: DeletePageInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeletePageTool;
