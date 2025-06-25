/**
 * Tool handler for creating a new book in Bookstack
 */
export async function handleCreateBook(server, args) {
    try {
        // Validate arguments
        if (!args.name || !args.description) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Name and description are required" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} to create book "${args.name}"`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        // Prepare payload
        const payload = {
            name: args.name,
            description: args.description
        };
        
        if (args.tags) {
            payload.tags = args.tags;
        }
        
        if (args.image_id) {
            payload.image_id = args.image_id;
        }

        try {
            // Set up timeout with AbortController
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout
            
            // Make the API request
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/books`, {
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
 * Tool definition for create_book
 */
export const createBookToolDefinition = {
    name: 'create_book',
    description: 'Creates a new book in Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
                description: 'The name of the book',
            },
            description: {
                type: 'string',
                description: 'A description of the book',
            },
            tags: {
                type: 'array',
                items: {
                    type: 'object'
                },
                description: 'A list of tag objects (each with "name" and "value")',
            },
            image_id: {
                type: 'number',
                description: 'The ID of an image to use as the cover',
            },
        },
        required: ['name', 'description'],
    },
};