const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');

const connectDB = async () => {
    try {
        const atlasUri = process.env.MONGO_URI;
        
        // 1. Try real Atlas Connection
        console.log('📡 Connecting to MongoDB Atlas...');
        await mongoose.connect(atlasUri, {
            serverSelectionTimeoutMS: 5000, // Faster timeout for local fallback
        });
        console.log('✅ MongoDB Atlas connected successfully.');
    } catch (err) {
        console.warn('⚠️ MongoDB Atlas connection failed:', err.message);
        
        // 2. Fallback to In-Memory MongoDB for Local Dev
        if (err.message.includes('ECONNREFUSED') || err.message.includes('querySrv')) {
            console.log('🔄 Starting In-Memory MongoDB for Local Development Mode...');
            try {
                const mongod = await MongoMemoryServer.create();
                const uri = mongod.getUri();
                
                await mongoose.connect(uri);
                console.log('🚀 Local In-Memory MongoDB is ACTIVE at:', uri);
                console.log('ℹ️  Note: Data will be lost when the server restarts.');
            } catch (innerErr) {
                console.error('❌ Failed to start In-Memory MongoDB:', innerErr.message);
                process.exit(1);
            }
        } else {
            console.error('❌ Critical MongoDB Error. Exiting...');
            process.exit(1);
        }
    }
};

module.exports = connectDB;
