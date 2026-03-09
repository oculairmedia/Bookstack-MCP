import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ListPagesInput = z.infer<typeof schema>;
declare class BookstackListPagesTool extends BookstackTool<ListPagesInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ListPagesInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackListPagesTool;
