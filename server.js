// Apollo Server + resolvers that run SQL (no business logic beyond CRUD)
const fs = require('fs');
const path = require('path');
const express = require('express');
const { ApolloServer } = require('@apollo/server');
const { expressMiddleware } = require('@apollo/server/express4');
const { GraphQLError } = require('graphql');
const db = require('./db');

const typeDefs = fs.readFileSync(path.join(__dirname, 'schema.graphql'), 'utf8');
const toDish = r => ({ id: r.id, name: r.name, price: Number(r.price), category: r.category ?? null, available: !!r.available });
const COLS = 'id, name, price, category, available';

const resolvers = {
  Query: {
    // dishes(available: true)  ->  WHERE available = ?
    dishes: async (_, { available }) => {
      const d = await db.init();
      const where = available === null || available === undefined ? '' : 'WHERE available = ?';
      const { rows } = await d.query(`SELECT ${COLS} FROM dishes ${where} ORDER BY id`, where ? [available ? 1 : 0] : []);
      return rows.map(toDish);
    },
    // dish(id: 2)  ->  WHERE id = ?
    dish: async (_, { id }) => {
      const d = await db.init();
      const { rows } = await d.query(`SELECT ${COLS} FROM dishes WHERE id = ?`, [Number(id)]);
      return rows[0] ? toDish(rows[0]) : null;
    }
  },
  Mutation: {
    // this resolver runs the INSERT
    addDish: async (_, { input }) => {
      if (!input.name.trim()) throw new GraphQLError('name must not be empty', { extensions: { code: 'BAD_USER_INPUT' } });
      if (!(input.price > 0)) throw new GraphQLError('price must be positive', { extensions: { code: 'BAD_USER_INPUT' } });
      const d = await db.init();
      const { insertId } = await d.query('INSERT INTO dishes (name, price, category, available) VALUES (?, ?, ?, ?)',
        [input.name.trim(), input.price, input.category ?? null, input.available === false ? 0 : 1]);
      const { rows } = await d.query(`SELECT ${COLS} FROM dishes WHERE id = ?`, [insertId]);
      return toDish(rows[0]);
    }
  }
};

(async () => {
  const d = await db.init();
  const server = new ApolloServer({ typeDefs, resolvers });
  await server.start();
  const app = express();
  app.use('/graphql', express.json(), expressMiddleware(server));
  app.use(express.static(path.join(__dirname, 'public')));
  const port = +process.env.PORT || 4000;
  app.listen(port, () => console.log(`\n  Menu GraphQL running (${d.kind})  ->  http://localhost:${port}   (endpoint: /graphql)\n`));
})();
