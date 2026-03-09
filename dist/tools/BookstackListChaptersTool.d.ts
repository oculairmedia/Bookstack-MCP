import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ListChaptersInput = z.infer<typeof schema>;
declare class BookstackListChaptersTool extends BookstackTool<ListChaptersInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: ListChaptersInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackListChaptersTool;
