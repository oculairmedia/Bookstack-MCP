import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type DeleteChapterInput = z.infer<typeof schema>;
declare class BookstackDeleteChapterTool extends BookstackTool<DeleteChapterInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: DeleteChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeleteChapterTool;
