import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ListBookshelvesInput = z.infer<typeof schema>;
declare class BookstackListBookshelvesTool extends BookstackTool<ListBookshelvesInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ListBookshelvesInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackListBookshelvesTool;
