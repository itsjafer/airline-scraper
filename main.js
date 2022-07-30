import { unitedFunc } from "./united.js";
import { aaFunc } from "./aa.js";
import Busboy from 'busboy'

const airlineToFunc = {
    "united": unitedFunc,
    "aa": aaFunc
}

const response = async(req, res, func) => {
    res.set('Access-Control-Allow-Origin', '*');
  
    if (req.method === 'OPTIONS') {
      // Send response to OPTIONS requests
      res.set('Access-Control-Allow-Methods', 'POST');
      res.set('Access-Control-Allow-Headers', 'Content-Type');
      res.set('Access-Control-Max-Age', '3600');
      return res.status(204).send('');
    }
    if (req.method !== 'POST') {
      // Return a "method not allowed" error
      return res.status(405).end();
    }
  
    const busboy = Busboy({headers: req.headers});
    const fields = {};
  
    // This code will process each non-file field in the form.
    busboy.on('field', (fieldname, val) => {
      console.log(`Processed field ${fieldname}: ${val}.`);
      fields[fieldname] = val;
    });
  
    busboy.end(req.rawBody);
  
    let flights = await airlineToFunc[func](fields['origin'], fields['destination'], fields['date'])
    res.status(200).send(flights);
}

export const united = async (req, res) => {
  return await response(req, res, "united")
}

export const aa = async (req, res) => {
    return await response(req, res, "aa")
}