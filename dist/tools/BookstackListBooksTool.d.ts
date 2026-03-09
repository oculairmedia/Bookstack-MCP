import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ListBooksInput = z.infer<typeof schema>;
declare class BookstackListBooksTool extends BookstackTool<ListBooksInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ListBooksInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackListBooksTool;
