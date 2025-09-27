import { handleCreateBook, createBookToolDefinition } from './create-book.js';
import { handleCreateBookshelf, createBookshelfToolDefinition } from './create-bookshelf.js';
import { handleCreateChapter, createChapterToolDefinition } from './create-chapter.js';
import { handleCreatePage, createPageToolDefinition } from './create-page.js';
import { handleDeleteBook, deleteBookToolDefinition } from './delete-book.js';
import { handleDeleteBookshelf, deleteBookshelfToolDefinition } from './delete-bookshelf.js';
import { handleDeleteChapter, deleteChapterToolDefinition } from './delete-chapter.js';
import { handleDeletePage, deletePageToolDefinition } from './delete-page.js';
import { handleListBooks, listBooksToolDefinition } from './list-books.js';
import { handleListBookshelves, listBookshelvesToolDefinition } from './list-bookshelves.js';
import { handleListChapters, listChaptersToolDefinition } from './list-chapters.js';
import { handleListPages, listPagesToolDefinition } from './list-pages.js';
import { handleReadBook, readBookToolDefinition } from './read-book.js';
import { handleReadBookshelf, readBookshelfToolDefinition } from './read-bookshelf.js';
import { handleReadChapter, readChapterToolDefinition } from './read-chapter.js';
import { handleReadPage, readPageToolDefinition } from './read-page.js';
import { handleUpdateBook, updateBookToolDefinition } from './update-book.js';
import { handleUpdateBookshelf, updateBookshelfToolDefinition } from './update-bookshelf.js';
import { handleUpdateChapter, updateChapterToolDefinition } from './update-chapter.js';
import { handleUpdatePage, updatePageToolDefinition } from './update-page.js';
import { CallToolRequestSchema, ListToolsRequestSchema, McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';

/**
 * Register all tool handlers with the server
 * @param {Object} server - The BookstackServer instance
 */
export function registerToolHandlers(server) {
    // Register tool definitions
    server.server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [
            createBookToolDefinition,
            createBookshelfToolDefinition,
            createChapterToolDefinition,
            createPageToolDefinition,
            deleteBookToolDefinition,
            deleteBookshelfToolDefinition,
            deleteChapterToolDefinition,
            deletePageToolDefinition,
            listBooksToolDefinition,
            listBookshelvesToolDefinition,
            listChaptersToolDefinition,
            listPagesToolDefinition,
            readBookToolDefinition,
            readBookshelfToolDefinition,
            readChapterToolDefinition,
            readPageToolDefinition,
            updateBookToolDefinition,
            updateBookshelfToolDefinition,
            updateChapterToolDefinition,
            updatePageToolDefinition,
        ],
    }));

    // Register tool call handler
    server.server.setRequestHandler(CallToolRequestSchema, async (request) => {
        switch (request.params.name) {
            case 'create_book':
                return handleCreateBook(server, request.params.arguments);
            case 'create_bookshelf':
                return handleCreateBookshelf(server, request.params.arguments);
            case 'create_chapter':
                return handleCreateChapter(server, request.params.arguments);
            case 'create_page':
                return handleCreatePage(server, request.params.arguments);
            case 'delete_book':
                return handleDeleteBook(server, request.params.arguments);
            case 'delete_bookshelf':
                return handleDeleteBookshelf(server, request.params.arguments);
            case 'delete_chapter':
                return handleDeleteChapter(server, request.params.arguments);
            case 'delete_page':
                return handleDeletePage(server, request.params.arguments);
            case 'list_books':
                return handleListBooks(server, request.params.arguments);
            case 'list_bookshelves':
                return handleListBookshelves(server, request.params.arguments);
            case 'list_chapters':
                return handleListChapters(server, request.params.arguments);
            case 'list_pages':
                return handleListPages(server, request.params.arguments);
            case 'read_book':
                return handleReadBook(server, request.params.arguments);
            case 'read_bookshelf':
                return handleReadBookshelf(server, request.params.arguments);
            case 'read_chapter':
                return handleReadChapter(server, request.params.arguments);
            case 'read_page':
                return handleReadPage(server, request.params.arguments);
            case 'update_book':
                return handleUpdateBook(server, request.params.arguments);
            case 'update_bookshelf':
                return handleUpdateBookshelf(server, request.params.arguments);
            case 'update_chapter':
                return handleUpdateChapter(server, request.params.arguments);
            case 'update_page':
                return handleUpdatePage(server, request.params.arguments);
            default:
                throw new McpError(
                    ErrorCode.MethodNotFound,
                    `Unknown tool: ${request.params.name}`
                );
        }
    });
}

// Export all tool definitions
export const toolDefinitions = [
    createBookToolDefinition,
    createBookshelfToolDefinition,
    createChapterToolDefinition,
    createPageToolDefinition,
    deleteBookToolDefinition,
    deleteBookshelfToolDefinition,
    deleteChapterToolDefinition,
    deletePageToolDefinition,
    listBooksToolDefinition,
    listBookshelvesToolDefinition,
    listChaptersToolDefinition,
    listPagesToolDefinition,
    readBookToolDefinition,
    readBookshelfToolDefinition,
    readChapterToolDefinition,
    readPageToolDefinition,
    updateBookToolDefinition,
    updateBookshelfToolDefinition,
    updateChapterToolDefinition,
    updatePageToolDefinition,
];

// Export all tool handlers
export const toolHandlers = {
    handleCreateBook,
    handleCreateBookshelf,
    handleCreateChapter,
    handleCreatePage,
    handleDeleteBook,
    handleDeleteBookshelf,
    handleDeleteChapter,
    handleDeletePage,
    handleListBooks,
    handleListBookshelves,
    handleListChapters,
    handleListPages,
    handleReadBook,
    handleReadBookshelf,
    handleReadChapter,
    handleReadPage,
    handleUpdateBook,
    handleUpdateBookshelf,
    handleUpdateChapter,
    handleUpdatePage,
};