import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type CreateChapterInput = z.infer<typeof schema>;
declare class BookstackCreateChapterTool extends BookstackTool<CreateChapterInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: CreateChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreateChapterTool;
