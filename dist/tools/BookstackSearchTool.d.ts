import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type BookstackSearchInput = z.infer<typeof schema>;
declare class BookstackSearchTool extends BookstackTool<BookstackSearchInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: BookstackSearchInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
    private createSearchResult;
    private extractSummary;
    private trimSummary;
    private asString;
}
export default BookstackSearchTool;
