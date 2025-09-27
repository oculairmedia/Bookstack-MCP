/**
 * Tool handler for creating a new page in Bookstack
 */
export async function handleCreatePage(server, args) {
    try {
        // Validate arguments
        if (!args.name) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Page name is required" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (!args.book_id && !args.chapter_id) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Either book_id or chapter_id is required" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (args.book_id && args.chapter_id) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Cannot specify both book_id and chapter_id" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (!args.markdown && !args.html) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Either markdown or html content is required" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (args.markdown && args.html) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Cannot specify both markdown and html content" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} to create page "${args.name}"`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        // Prepare payload
        const payload = {
            name: args.name
        };
        
        if (args.book_id) {
            payload.book_id = args.book_id;
        }
        
        if (args.chapter_id) {
            payload.chapter_id = args.chapter_id;
        }
        
        if (args.markdown) {
            payload.markdown = args.markdown;
        }
        
        if (args.html) {
            payload.html = args.html;
        }
        
        if (args.tags) {
            payload.tags = args.tags;
        }
        
        if (args.priority !== undefined) {
            payload.priority = args.priority;
        }

        try {
            // Set up timeout with AbortController
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout
            
            // Make the API request
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/pages`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            
            // Clear the timeout
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify(data, null, 2),
                }],
            };
        } catch (error) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ 
                        error: `Network or HTTP error - ${error.message}` 
                    }, null, 2),
                }],
                isError: true
            };
        }
    } catch (error) {
        return server.createErrorResponse(error);
    }
}

/**
 * Tool definition for create_page
 */
export const createPageToolDefinition = {
    name: 'create_page',
    description: 'Creates a new page in Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
                description: 'The name of the page',
            },
            book_id: {
                type: 'number',
                description: 'The ID of the book to create the page in',
            },
            chapter_id: {
                type: 'number',
                description: 'The ID of the chapter to create the page in',
            },
            markdown: {
                type: 'string',
                description: 'The page content in Markdown format',
            },
            html: {
                type: 'string',
                description: 'The page content in HTML format',
            },
            tags: {
                type: 'array',
                items: {
                    type: 'object',
                    properties: {
                        name: { type: 'string' },
                        value: { type: 'string' }
                    },
                    required: ['name', 'value'],
                    additionalProperties: false
                },
                description: 'A list of tag objects (each with "name" and "value")',
            },
            priority: {
                type: 'number',
                description: 'Page priority',
            },
        },
        required: ['name'],
    },
};