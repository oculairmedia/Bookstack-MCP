/**
 * Tool handler for creating a new chapter in Bookstack
 */
export async function handleCreateChapter(server, args) {
    try {
        // Validate arguments
        if (!args.book_id || typeof args.book_id !== 'number' || args.book_id <= 0) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Valid book ID is required" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (!args.name) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Chapter name is required" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} to create chapter "${args.name}" in book ID ${args.book_id}`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        // Prepare payload
        const payload = {
            book_id: args.book_id,
            name: args.name
        };
        
        if (args.description) {
            payload.description = args.description;
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
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/chapters`, {
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
 * Tool definition for create_chapter
 */
export const createChapterToolDefinition = {
    name: 'create_chapter',
    description: 'Creates a new chapter in Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            book_id: {
                type: 'number',
                description: 'The ID of the book to create the chapter in',
            },
            name: {
                type: 'string',
                description: 'The name of the chapter',
            },
            description: {
                type: 'string',
                description: 'A description of the chapter',
            },
            tags: {
                type: 'array',
                items: {
                    type: 'object'
                },
                description: 'A list of tag objects (each with "name" and "value")',
            },
            priority: {
                type: 'number',
                description: 'Chapter priority',
            },
        },
        required: ['book_id', 'name'],
    },
};