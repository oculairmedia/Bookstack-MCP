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
import { handleSearchBookstack, searchBookstackToolDefinition } from './search-bookstack.js';
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
            searchBookstackToolDefinition,
        ],
    }));

    // Register tool call handler
    server.server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const args = (request.params.arguments && typeof request.params.arguments === 'object')
            ? request.params.arguments
            : {};

        switch (request.params.name) {
            case 'create_book':
                return handleCreateBook(server, args);
            case 'create_bookshelf':
                return handleCreateBookshelf(server, args);
            case 'create_chapter':
                return handleCreateChapter(server, args);
            case 'create_page':
                return handleCreatePage(server, args);
            case 'delete_book':
                return handleDeleteBook(server, args);
            case 'delete_bookshelf':
                return handleDeleteBookshelf(server, args);
            case 'delete_chapter':
                return handleDeleteChapter(server, args);
            case 'delete_page':
                return handleDeletePage(server, args);
            case 'list_books':
                return handleListBooks(server, args);
            case 'list_bookshelves':
                return handleListBookshelves(server, args);
            case 'list_chapters':
                return handleListChapters(server, args);
            case 'list_pages':
                return handleListPages(server, args);
            case 'read_book':
                return handleReadBook(server, args);
            case 'read_bookshelf':
                return handleReadBookshelf(server, args);
            case 'read_chapter':
                return handleReadChapter(server, args);
            case 'read_page':
                return handleReadPage(server, args);
            case 'update_book':
                return handleUpdateBook(server, args);
            case 'update_bookshelf':
                return handleUpdateBookshelf(server, args);
            case 'update_chapter':
                return handleUpdateChapter(server, args);
            case 'update_page':
                return handleUpdatePage(server, args);
            case 'search_bookstack':
                return handleSearchBookstack(server, args);
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
    searchBookstackToolDefinition,
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
    handleSearchBookstack,
};
