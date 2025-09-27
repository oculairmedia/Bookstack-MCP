#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

/**
 * Core BookstackServer class that handles initialization and API communication
 */
export class BookstackServer {
    /**
     * Initialize the Bookstack MCP server
     */
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

    /**
     * Get API headers with authentication
     * @returns {Object} Headers object
     */
    getApiHeaders() {
        return {
            'Authorization': `Token ${this.tokenId}:${this.tokenSecret}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };
    }

    /**
     * Create a standard error response
     * @param {Error} error - The error object
     * @returns {Object} Formatted error response
     */
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
}