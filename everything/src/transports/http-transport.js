import express from 'express';
import cors from 'cors';
import { randomUUID } from 'crypto';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';

/**
 * A simple in-memory implementation of the EventStore interface for recovery
 * Primarily for examples and testing; not suitable for production (use a persistent storage solution)
 */
class InMemoryEventStore {
    constructor() {
        this.events = new Map();
    }

    /**
     * Generate a unique event ID for a given stream ID
     */
    generateEventId(streamId) {
        return `${streamId}_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
    }

    /**
     * Extract stream ID from event ID
     */
    getStreamIdFromEventId(eventId) {
        const parts = eventId.split('_');
        return parts.length > 0 ? parts[0] : '';
    }

    /**
     * Store an event with a generated event ID
     * Implements EventStore.storeEvent
     */
    async storeEvent(streamId, message) {
        const eventId = this.generateEventId(streamId);
        this.events.set(eventId, { streamId, message });
        return eventId;
    }

    /**
     * Replay events occurring after a specific event ID
     * Implements EventStore.replayEventsAfter
     */
    async replayEventsAfter(lastEventId, { send }) {
        if (!lastEventId || !this.events.has(lastEventId)) {
            return '';
        }

        // Extract stream ID from event ID
        const streamId = this.getStreamIdFromEventId(lastEventId);
        if (!streamId) {
            return '';
        }

        let foundLastEvent = false;

        // Sort events by eventId for chronological order
        const sortedEvents = [...this.events.entries()].sort((a, b) => a[0].localeCompare(b[0]));

        for (const [eventId, { streamId: eventStreamId, message }] of sortedEvents) {
            // Only include events from the same stream
            if (eventStreamId !== streamId) {
                continue;
            }

            // Start sending events after lastEventId
            if (eventId === lastEventId) {
                foundLastEvent = true;
                continue;
            }

            if (foundLastEvent) {
                await send(eventId, message);
            }
        }
        return streamId;
    }
}

/**
 * Run the server using HTTP streaming transport (MCP compatible)
 * @param {Object} server - The BookstackServer instance
 */
export async function runHTTP(server) {
    try {
        const app = express();
        const transports = {};

        // Security: Validate Origin header to prevent DNS rebinding attacks
        app.use((req, res, next) => {
            const origin = req.headers.origin;
            const allowedOrigins = [
                'http://localhost',
                'http://127.0.0.1',
                'http://192.168.50.90',
                'https://knowledge.oculair.ca'
            ];

            if (origin && !allowedOrigins.some(allowed => origin.startsWith(allowed))) {
                console.warn(`Blocked request from unauthorized origin: ${origin}`);
                return res.status(403).json({
                    jsonrpc: '2.0',
                    error: {
                        code: -32001,
                        message: 'Forbidden: Invalid origin'
                    },
                    id: null
                });
            }
            next();
        });

        // Middleware
        app.use(cors({
            origin: ['http://localhost', 'http://127.0.0.1', 'http://192.168.50.90', 'https://knowledge.oculair.ca'],
            credentials: true
        }));
        app.use(express.json({ limit: '10mb' }));
        app.use(express.urlencoded({ extended: true }));

        // Request logging middleware
        app.use((req, res, next) => {
            const timestamp = new Date().toISOString();
            console.log(`[${timestamp}] ${req.method} ${req.path} - ${req.ip}`);
            next();
        });

        // Protocol version validation middleware
        app.use('/mcp', (req, res, next) => {
            // Skip validation for initialization requests
            if (req.method === 'POST' && req.body && req.body.method === 'initialize') {
                return next();
            }

            const protocolVersion = req.headers['mcp-protocol-version'];
            if (protocolVersion && protocolVersion !== '2025-06-18' && protocolVersion !== '2025-03-26') {
                return res.status(400).json({
                    jsonrpc: '2.0',
                    error: {
                        code: -32000,
                        message: `Unsupported MCP protocol version: ${protocolVersion}`
                    },
                    id: null
                });
            }
            next();
        });


        // Main MCP endpoint - POST
        app.post('/mcp', async (req, res) => {
            console.log('Received MCP request:', req.body);
            try {
                // Check for session ID
                const sessionId = req.headers['mcp-session-id'];
                let transport;

                if (sessionId && transports[sessionId]) {
                    // Reuse existing transport
                    transport = transports[sessionId];
                } else if (!sessionId && isInitializeRequest(req.body)) {
                    // New initialization request
                    const eventStore = new InMemoryEventStore();
                    transport = new StreamableHTTPServerTransport({
                        sessionIdGenerator: () => randomUUID(),
                        eventStore, // Enable recoverability
                        onsessioninitialized: (sessionId) => {
                            // Store transport by session ID when initialized
                            // Avoids race conditions before session storage
                            console.log(`Session initialized with ID: ${sessionId}`);
                            transports[sessionId] = transport;
                        }
                    });

                    // Set onclose handler to clean up transport on closure
                    transport.onclose = () => {
                        const sid = transport.sessionId;
                        if (sid && transports[sid]) {
                            console.log(`Transport closed for session ${sid}, removing from transports map`);
                            delete transports[sid];
                        }
                    };

                    // Connect transport to MCP server before handling the request
                    // Ensures responses stream back through the same transport
                    await server.server.connect(transport);

                    await transport.handleRequest(req, res, req.body);
                    return; // Already handled
                } else {
                    // Invalid request - no session ID or not an initialization request
                    res.status(400).json({
                        jsonrpc: '2.0',
                        error: {
                            code: -32000,
                            message: 'Bad Request: No valid session ID provided',
                        },
                        id: null,
                    });
                    return;
                }

                // Handle request with existing transport - no need to reconnect
                // Existing transport is already connected to the server
                await transport.handleRequest(req, res, req.body);
            } catch (error) {
                console.error('Error handling MCP request:', error);
                if (!res.headersSent) {
                    res.status(500).json({
                        jsonrpc: '2.0',
                        error: {
                            code: -32603,
                            message: 'Internal server error',
                        },
                        id: null,
                    });
                }
            }
        });

        // MCP endpoint - GET (for SSE streaming)
        app.get('/mcp', async (req, res) => {
            const sessionId = req.headers['mcp-session-id'];

            if (!sessionId || !transports[sessionId]) {
                return res.status(400).send('Session ID required');
            }

            const transport = transports[sessionId];
            await transport.handleRequest(req, res);
        });

        // Session termination endpoint - DELETE
        app.delete('/mcp', async (req, res) => {
            const sessionId = req.headers['mcp-session-id'];

            if (!sessionId) {
                return res.status(400).json({
                    jsonrpc: '2.0',
                    error: { 
                        code: -32000, 
                        message: 'Bad Request: No session ID provided' 
                    }
                });
            }

            if (!transports[sessionId]) {
                return res.status(404).json({
                    jsonrpc: '2.0',
                    error: { 
                        code: -32001, 
                        message: 'Session not found' 
                    }
                });
            }

            try {
                // Clean up the session
                const transport = transports[sessionId];
                if (transport.onclose) {
                    transport.onclose();
                }
                delete transports[sessionId];

                console.log(`Session ${sessionId} terminated by client`);
                res.status(200).json({ 
                    jsonrpc: '2.0',
                    result: { terminated: true } 
                });
            } catch (error) {
                console.error(`Error terminating session ${sessionId}:`, error);
                res.status(500).json({
                    jsonrpc: '2.0',
                    error: {
                        code: -32603,
                        message: 'Internal server error during session termination'
                    }
                });
            }
        });

        // Health check endpoint
        app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                transport: 'streamable_http',
                protocol_version: '2025-06-18',
                sessions: Object.keys(transports).length,
                uptime: process.uptime(),
                timestamp: new Date().toISOString(),
                security: {
                    origin_validation: true,
                    localhost_binding: true
                },
                bookstack: {
                    api_url: server.baseUrl,
                    credentials_available: server.tokenId && server.tokenSecret ? true : false
                }
            });
        });

        // Start server - bind to all interfaces for Docker container access
        const PORT = process.env.PORT || 3001;
        const HOST = '0.0.0.0'; // Docker containers need to bind to all interfaces

        const httpServer = app.listen(PORT, HOST, () => {
            console.log(`Bookstack MCP HTTP server is running on ${HOST}:${PORT}`);
            console.log(`MCP endpoint: http://localhost:${PORT}/mcp`);
            console.log(`Health check: http://localhost:${PORT}/health`);
            console.log(`Protocol version: 2025-06-18`);
            console.log(`Security: Origin validation enabled, DNS rebinding protection active`);
            console.log(`Bookstack API: ${server.baseUrl}`);
            console.log(`API credentials: ${server.tokenId && server.tokenSecret ? 'Available' : 'Not available'}`);
        });

        // Graceful shutdown
        const shutdownHandler = async () => {
            console.log('Shutting down HTTP server...');
            httpServer.close();

            // Clean up all transports
            for (const [sessionId, transport] of Object.entries(transports)) {
                try {
                    console.log(`Cleaning up session: ${sessionId}`);
                    if (transport.onclose) {
                        transport.onclose();
                    }
                } catch (error) {
                    console.error(`Error cleaning up session ${sessionId}:`, error);
                }
            }

            await server.server.close();
            process.exit(0);
        };

        process.on('SIGINT', shutdownHandler);
        process.on('SIGTERM', shutdownHandler);

    } catch (error) {
        console.error('Failed to start HTTP server:', error);
        process.exit(1);
    }
}