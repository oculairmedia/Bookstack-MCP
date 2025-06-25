#!/usr/bin/env node
import dotenv from 'dotenv';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { CallToolRequestSchema, ListToolsRequestSchema, McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';
import express from 'express';
import axios from 'axios';

// Import Bookstack tool handlers and definitions
import { handleCreateBook, createBookToolDefinition } from './src/tools/create-book.js';
import { handleReadBook, readBookToolDefinition } from './src/tools/read-book.js';
import { handleUpdateBook, updateBookToolDefinition } from './src/tools/update-book.js';
import { handleDeleteBook, deleteBookToolDefinition } from './src/tools/delete-book.js';
import { handleListBooks, listBooksToolDefinition } from './src/tools/list-books.js';

import { handleCreateBookshelf, createBookshelfToolDefinition } from './src/tools/create-bookshelf.js';
import { handleReadBookshelf, readBookshelfToolDefinition } from './src/tools/read-bookshelf.js';
import { handleUpdateBookshelf, updateBookshelfToolDefinition } from './src/tools/update-bookshelf.js';
import { handleDeleteBookshelf, deleteBookshelfToolDefinition } from './src/tools/delete-bookshelf.js';
import { handleListBookshelves, listBookshelvesToolDefinition } from './src/tools/list-bookshelves.js';

import { handleCreateChapter, createChapterToolDefinition } from './src/tools/create-chapter.js';
import { handleReadChapter, readChapterToolDefinition } from './src/tools/read-chapter.js';
import { handleUpdateChapter, updateChapterToolDefinition } from './src/tools/update-chapter.js';
import { handleDeleteChapter, deleteChapterToolDefinition } from './src/tools/delete-chapter.js';
import { handleListChapters, listChaptersToolDefinition } from './src/tools/list-chapters.js';

import { handleCreatePage, createPageToolDefinition } from './src/tools/create-page.js';
import { handleReadPage, readPageToolDefinition } from './src/tools/read-page.js';
import { handleUpdatePage, updatePageToolDefinition } from './src/tools/update-page.js';
import { handleDeletePage, deletePageToolDefinition } from './src/tools/delete-page.js';
import { handleListPages, listPagesToolDefinition } from './src/tools/list-pages.js';

// Load environment variables
dotenv.config();

class BookstackServer {
    constructor() {
        // Initialize MCP server
        this.server = new Server({
            name: 'bookstack-server',
            version: '1.0.0',
        }, {
            capabilities: {
                tools: {},
            },
        });

        // Set up error handler
        this.server.onerror = (error) => console.error('[MCP Error]', error);

        // Set up tool handlers
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                createBookToolDefinition,
                readBookToolDefinition,
                updateBookToolDefinition,
                deleteBookToolDefinition,
                listBooksToolDefinition,
                
                createBookshelfToolDefinition,
                readBookshelfToolDefinition,
                updateBookshelfToolDefinition,
                deleteBookshelfToolDefinition,
                listBookshelvesToolDefinition,
                
                createChapterToolDefinition,
                readChapterToolDefinition,
                updateChapterToolDefinition,
                deleteChapterToolDefinition,
                listChaptersToolDefinition,
                
                createPageToolDefinition,
                readPageToolDefinition,
                updatePageToolDefinition,
                deletePageToolDefinition,
                listPagesToolDefinition,
            ],
        }));

        // Set up CallTool handler
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            switch (request.params.name) {
                case 'create_book':
                    return handleCreateBook(this, request.params.arguments);
                case 'read_book':
                    return handleReadBook(this, request.params.arguments);
                case 'update_book':
                    return handleUpdateBook(this, request.params.arguments);
                case 'delete_book':
                    return handleDeleteBook(this, request.params.arguments);
                case 'list_books':
                    return handleListBooks(this, request.params.arguments);
                    
                case 'create_bookshelf':
                    return handleCreateBookshelf(this, request.params.arguments);
                case 'read_bookshelf':
                    return handleReadBookshelf(this, request.params.arguments);
                case 'update_bookshelf':
                    return handleUpdateBookshelf(this, request.params.arguments);
                case 'delete_bookshelf':
                    return handleDeleteBookshelf(this, request.params.arguments);
                case 'list_bookshelves':
                    return handleListBookshelves(this, request.params.arguments);
                    
                case 'create_chapter':
                    return handleCreateChapter(this, request.params.arguments);
                case 'read_chapter':
                    return handleReadChapter(this, request.params.arguments);
                case 'update_chapter':
                    return handleUpdateChapter(this, request.params.arguments);
                case 'delete_chapter':
                    return handleDeleteChapter(this, request.params.arguments);
                case 'list_chapters':
                    return handleListChapters(this, request.params.arguments);
                    
                case 'create_page':
                    return handleCreatePage(this, request.params.arguments);
                case 'read_page':
                    return handleReadPage(this, request.params.arguments);
                case 'update_page':
                    return handleUpdatePage(this, request.params.arguments);
                case 'delete_page':
                    return handleDeletePage(this, request.params.arguments);
                case 'list_pages':
                    return handleListPages(this, request.params.arguments);
                    
                default:
                    throw new McpError(
                        ErrorCode.MethodNotFound,
                        `Unknown tool: ${request.params.name}`
                    );
            }
        });

        // Initialize API configuration
        this.baseUrl = process.env.BS_URL || 'https://knowledge.oculair.ca';
        this.tokenId = process.env.BS_TOKEN_ID;
        this.tokenSecret = process.env.BS_TOKEN_SECRET;
        
        if (!this.tokenId || !this.tokenSecret) {
            console.warn('Warning: BS_TOKEN_ID or BS_TOKEN_SECRET environment variables not set');
        }
        
        // Initialize axios instance for API requests
        this.api = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        });
    }

    // Helper method to get API headers with authentication
    getApiHeaders() {
        return {
            'Authorization': `Token ${this.tokenId}:${this.tokenSecret}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };
    }

    // Helper method to create error responses
    createErrorResponse(error) {
        console.error('Error in tool handler:', error);
        return {
            content: [{
                type: 'text',
                text: JSON.stringify({
                    success: false,
                    error: error.message,
                    details: error.response?.data || error,
                }, null, 2),
            }],
            isError: true,
        };
    }

    async runStdio() {
        try {
            const transport = new StdioServerTransport();
            await this.server.connect(transport);
            console.error('Bookstack MCP server running on stdio');

            const cleanup = async () => {
                await this.server.close();
                process.exit(0);
            };

            process.on('SIGINT', cleanup);
            process.on('SIGTERM', cleanup);
            process.on('uncaughtException', async (error) => {
                console.error('Uncaught exception:', error);
                await cleanup();
            });
        } catch (err) {
            const error = err instanceof Error ? err : new Error(String(err));
            console.error('Failed to start server:', error);
            process.exit(1);
        }
    }

    async runSSE() {
        try {
            const app = express();
            let transport;
            let activeConnections = new Map();
            
            app.get('/sse', async (req, res) => {
                console.log('Received SSE connection');
                
                // Set headers for SSE
                res.setHeader('Content-Type', 'text/event-stream');
                res.setHeader('Cache-Control', 'no-cache');
                res.setHeader('Connection', 'keep-alive');
                
                // Generate client ID
                const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`;
                
                transport = new SSEServerTransport('/message', res);
                await this.server.connect(transport);
                
                // Store connection info
                activeConnections.set(clientId, {
                    transport,
                    connectedAt: new Date(),
                    req,
                    res
                });
                
                console.log(`SSE connection established for client ${clientId}`);
                console.log(`Active connections: ${activeConnections.size}`);
                
                // Send initial connected message
                res.write(': connected\n\n');
                
                req.on('close', () => {
                    console.log(`SSE connection closed for client ${clientId}`);
                    activeConnections.delete(clientId);
                    console.log(`Connection lost, waiting for new client connection to reconnect...`);
                });
                
                this.server.onclose = async () => {
                    console.log('Server closing...');
                    await this.server.close();
                };
            });
            
            app.post('/message', async (req, res) => {
                try {
                    console.log('Received message');
                    if (!transport) {
                        console.error('No active SSE connection');
                        res.status(503).json({ error: 'No active SSE connection' });
                        return;
                    }
                    await transport.handlePostMessage(req, res);
                } catch (error) {
                    console.error('Error handling message:', error);
                    res.status(500).json({ error: 'Internal server error' });
                }
            });
            
            // Add a health check endpoint
            app.get('/health', (req, res) => {
                res.json({
                    status: 'ok',
                    activeConnections: activeConnections.size,
                    uptime: process.uptime()
                });
            });
            
            // Set up a ping interval to keep connections alive
            const pingInterval = setInterval(() => {
                if (activeConnections.size > 0) {
                    console.log(`Sending ping to ${activeConnections.size} active connections`);
                    
                    for (const [clientId, connection] of activeConnections.entries()) {
                        try {
                            if (connection.res && !connection.res.finished) {
                                connection.res.write(': ping\n\n');
                            }
                        } catch (error) {
                            console.error(`Error sending ping to client ${clientId}:`, error);
                            activeConnections.delete(clientId);
                        }
                    }
                }
            }, 30000); // Send ping every 30 seconds
            
            const PORT = process.env.PORT || 3001;
            const httpServer = app.listen(PORT, () => {
                console.log(`Bookstack MCP server running on port ${PORT}`);
                console.log(`Bookstack API: ${this.baseUrl}`);
                console.log(`Connection tracking: enabled with ping interval (30s)`);
            });
            
            const cleanup = async () => {
                console.log('Starting cleanup process...');
                
                // Clear the ping interval
                console.log('Clearing ping interval');
                clearInterval(pingInterval);
                
                // Clean up all active connections
                console.log(`Cleaning up ${activeConnections.size} active connections`);
                for (const [clientId, connection] of activeConnections.entries()) {
                    console.log(`Closing connection for client ${clientId}`);
                    activeConnections.delete(clientId);
                }
                
                // Close the HTTP server
                console.log('Closing HTTP server...');
                httpServer.close();
                
                // Close the MCP server
                console.log('Closing MCP server...');
                await this.server.close();
                
                console.log('Cleanup complete, exiting process');
                process.exit(0);
            };
            
            process.on('SIGINT', cleanup);
            process.on('SIGTERM', cleanup);
            process.on('uncaughtException', async (error) => {
                console.error('Uncaught exception:', error);
                await cleanup();
            });
        } catch (err) {
            const error = err instanceof Error ? err : new Error(String(err));
            console.error('Failed to start SSE server:', error);
            process.exit(1);
        }
    }
}

const server = new BookstackServer();
const useSSE = process.argv.includes('--sse');

if (useSSE) {
    server.runSSE().catch(console.error);
} else {
    server.runStdio().catch(console.error);
}
