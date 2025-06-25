/**
 * Tool handler for listing books from Bookstack API
 */
export async function handleListBooks(server, args) {
    try {
        // Handle tool info request
        if (args.offset === "__tool_info__") {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({
                        name: "list_books",
                        description: "Lists all books in Bookstack with pagination support",
                        args: {
                            offset: {
                                type: "int",
                                description: "Number of records to skip",
                                required: false
                            },
                            count: {
                                type: "int",
                                description: "Number of records to take",
                                required: false
                            }
                        }
                    }, null, 2),
                }],
            };
        }

        // Validate arguments
        const offset = typeof args.offset === 'number' ? args.offset : 0;
        const count = typeof args.count === 'number' ? args.count : 100;

        if (offset < 0) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Invalid offset value" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (count <= 0) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Invalid count value" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} with token ID ${tokenId}`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        // Set up request parameters
        const params = new URLSearchParams({
            offset: offset.toString(),
            count: count.toString()
        });

        try {
            // Set up timeout with AbortController
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout
            
            // Make the API request
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/books?${params.toString()}`, {
                method: 'GET',
                headers: headers,
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
 * Tool definition for list_books
 */
export const listBooksToolDefinition = {
    name: 'list_books',
    description: 'Lists all books in Bookstack with pagination support',
    inputSchema: {
        type: 'object',
        properties: {
            offset: {
                type: 'number',
                description: 'Number of records to skip',
            },
            count: {
                type: 'number',
                description: 'Number of records to take',
            },
        },
        required: [],
    },
};